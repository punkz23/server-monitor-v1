import requests
from urllib.parse import urljoin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SophosXGS126Client:
    """Client for interacting with Sophos XGS126 API"""
    
    def __init__(self, host, port, username, password, verify_ssl=False):
        self.base_url = f"https://{host}:{port}/"
        self.session = requests.Session()
        self.session.verify = verify_ssl
        # Disable SSL warnings for self-signed certificates
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.auth_token = None
        self.username = username
        self.password = password
        self.login(username, password)
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to API"""
        url = urljoin(self.base_url, endpoint)
        headers = {
            "Accept": "application/xml, text/xml, */*",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                data=data,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response content (first 500 chars): {response.text[:500]}")
            
            # Log full XML content for debugging
            if response.content and response.text.strip().startswith('<?xml'):
                logger.info(f"Full XML response from {endpoint}:")
                logger.info(response.text)
            
            if response.content:
                if response.text.strip().startswith('<?xml'):
                    return response.text
                else:
                    try:
                        return response.json()
                    except ValueError:
                        return response.text
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def login(self, username, password):
        """Authenticate and get session token"""
        # Try different XML formats for Sophos API authentication
        xml_formats = [
            # Format 1: Correct Login format from documentation
            f"""<Request>
    <Login>
        <Username>{username}</Username>
        <Password>{password}</Password>
    </Login>
</Request>""",
            
            # Format 2: With API version
            f"""<Request APIVersion="2105.1">
    <Login>
        <Username>{username}</Username>
        <Password>{password}</Password>
    </Login>
</Request>""",
            
            # Format 3: Basic authentication (current)
            f"""<Request>
    <Authentication>
        <Username>{username}</Username>
        <Password>{password}</Password>
    </Authentication>
</Request>""",
            
            # Format 4: With namespace
            f"""<Request xmlns="http://www.sophos.com/appliance">
    <Login>
        <Username>{username}</Username>
        <Password>{password}</Password>
    </Login>
</Request>""",
            
            # Format 5: With authentication type
            f"""<Request>
    <Login type="password">
        <Username>{username}</Username>
        <Password>{password}</Password>
    </Login>
</Request>""",
            
            # Format 6: XG style authentication
            f"""<Request>
    <Authentication>
        <Username>{username}</Username>
        <Password>{password}</Password>
    </Authentication>
</Request>"""
        ]
        
        for i, login_xml in enumerate(xml_formats, 1):
            try:
                logger.info(f"Trying XML format {i}...")
                response = self.session.post(
                    f"{self.base_url}webconsole/APIController",
                    data={'reqxml': login_xml},
                    verify=self.session.verify,
                    timeout=10
                )
                
                if response.status_code == 200 and response.text.startswith('<?xml'):
                    logger.info(f"Format {i} response: {response.text[:200]}...")
                    
                    # Check if authentication was successful
                    if '<Authentication/>' in response.text and 'Authentication Failure' not in response.text:
                        self.auth_token = True
                        logger.info(f"Successfully authenticated with Sophos XG API using format {i}")
                        # Store session cookies for subsequent requests
                        if response.cookies:
                            self.session.cookies.update(response.cookies)
                        return True
                    elif 'Authentication Failure' not in response.text and '<Login>' not in response.text:
                        # Check for other success indicators
                        if '<Response' in response.text and 'status' not in response.text:
                            self.auth_token = True
                            logger.info(f"Successfully authenticated with Sophos XG API using format {i}")
                            if response.cookies:
                                self.session.cookies.update(response.cookies)
                            return True
                else:
                    logger.debug(f"Format {i} failed with status: {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"Format {i} failed: {e}")
        
        logger.debug("All XML formats failed, trying form-based login")
        
        # Fallback to form-based authentication
        # For Sophos XG firewalls, use the exact form fields from the login page
        form_data = {
            "username": username,
            "password": password,
            "mode": "1"  # Standard login mode
        }
        
        # First, get the login page to establish session and get cookies
        try:
            session_response = self.session.get(f"{self.base_url}webconsole/", verify=self.session.verify, timeout=10)
            logger.debug(f"Login page status: {session_response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get login page: {e}")
            return False
        
        # Submit login form
        try:
            response = self.session.post(
                f"{self.base_url}webconsole/",
                data=form_data,
                verify=self.session.verify,
                timeout=10,
                allow_redirects=True
            )
            
            # Check if we got redirected or if the response indicates success
            if response.status_code in [200, 302]:
                # Try to access API endpoint to verify authentication
                api_test = self.session.get(
                    f"{self.base_url}webconsole/APIController?reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
                    verify=self.session.verify,
                    timeout=10
                )
                
                if api_test.status_code == 200 and api_test.text.startswith('<?xml'):
                    if 'Authentication Failure' not in api_test.text:
                        self.auth_token = True  # Session-based authentication successful
                        logger.info("Successfully authenticated with Sophos XG API using form-based method")
                        return True
                    else:
                        logger.error(f"API test shows authentication failure")
                        return False
                else:
                    logger.error(f"API test failed: {api_test.status_code}")
                    return False
            else:
                logger.error(f"Login failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Login request failed: {e}")
            return False

    def get_system_status(self):
        """Get system status and health"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": "<Request><Get><SystemStatus></SystemStatus></Get></Request>"})
    
    def get_interfaces(self):
        """Get network interfaces status"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": "<Request><Get><Interface></Interface></Get></Request>"})
    
    def get_firewall_sessions(self):
        """Get current firewall sessions"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": "<Request><Get><LiveConnection></LiveConnection></Get></Request>"})
    
    def get_vpn_status(self):
        """Get VPN tunnel status"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": "<Request><Get><IPSecVPN></IPSecVPN></Get></Request>"})
    
    def get_threat_prevention(self):
        """Get threat prevention status"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": "<Request><Get><ThreatPrevention></ThreatPrevention></Get></Request>"})
    
    def get_system_resources(self):
        """Get system resource usage (CPU, memory, etc.)"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": "<Request><Get><SystemResources></SystemResources></Get></Request>"})
    
    def get_firewall_rules(self):
        """Get firewall rules configuration"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": "<Request><Get><FirewallRule></FirewallRule></Get></Request>"})
    
    def get_security_events(self, limit=100):
        """Get recent security events"""
        return self._make_request("GET", "webconsole/APIController", params={"reqxml": f"<Request><Get><Logs><LogLimit>{limit}</LogLimit></Logs></Get></Request>"})
    
    def get_arp_table(self):
        """Get ARP table to see all connected devices"""
        if not self.auth_token:
            if not self.login(self.username, self.password):
                raise Exception("Not authenticated")
        
        # Use correct module names from Sophos documentation
        arp_xml = f"""<Request>
    <Login>
        <Username>{self.username}</Username>
        <Password>{self.password}</Password>
    </Login>
    <Get><IPHostStatistics></IPHostStatistics></Get>
</Request>"""
        
        return self._make_request("POST", "webconsole/APIController", data={'reqxml': arp_xml})
    
    def get_dhcp_leases(self):
        """Get DHCP lease table to see DHCP clients"""
        if not self.auth_token:
            if not self.login(self.username, self.password):
                raise Exception("Not authenticated")
        
        # Use correct module names from Sophos documentation
        dhcp_xml = f"""<Request>
    <Login>
        <Username>{self.username}</Username>
        <Password>{self.password}</Password>
    </Login>
    <Get><InterfaceStatistics></InterfaceStatistics></Get>
</Request>"""
        
        return self._make_request("POST", "webconsole/APIController", data={'reqxml': dhcp_xml})
    
    def get_active_connections(self):
        """Get active connections for additional device discovery"""
        if not self.auth_token:
            if not self.login(self.username, self.password):
                raise Exception("Not authenticated")
        
        # Use correct module names from Sophos documentation
        conn_xml = f"""<Request>
    <Login>
        <Username>{self.username}</Username>
        <Password>{self.password}</Password>
    </Login>
    <Get><GatewayStatistics></GatewayStatistics></Get>
</Request>"""
        
        return self._make_request("POST", "webconsole/APIController", data={'reqxml': conn_xml})
    
    def get_network_hosts(self, interface=None):
        """Get network hosts from the firewall's perspective"""
        if not self.auth_token:
            if not self.login(self.username, self.password):
                raise Exception("Not authenticated")
        
        # Use correct module names from Sophos documentation
        if interface:
            host_xml = f"""<Request>
    <Login>
        <Username>{self.username}</Username>
        <Password>{self.password}</Password>
    </Login>
    <Get><InterfaceStatistics></InterfaceStatistics></Get>
</Request>"""
        else:
            host_xml = f"""<Request>
    <Login>
        <Username>{self.username}</Username>
        <Password>{self.password}</Password>
    </Login>
    <Get><ZoneStatistics></ZoneStatistics></Get>
</Request>"""
        
        return self._make_request("POST", "webconsole/APIController", data={'reqxml': host_xml})
