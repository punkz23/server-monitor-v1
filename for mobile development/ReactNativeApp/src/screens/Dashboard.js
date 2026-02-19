import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import APIService from '../services/api';

const {width} = Dimensions.get('window');

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [serverStatus, setServerStatus] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [dashboardResponse, serverResponse] = await Promise.all([
        APIService.getDashboardSummary(),
        APIService.getServerStatus(),
      ]);
      
      setDashboardData(dashboardResponse);
      setServerStatus(serverResponse.servers || []);
    } catch (error) {
      console.log('Dashboard load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getStatusColor = (status) => {
    return status === 'UP' ? '#4CAF50' : '#F44336';
  };

  const MetricCard = ({title, value, subtitle, icon, color}) => (
    <View style={[styles.metricCard, {borderLeftColor: color}]}>
      <View style={styles.metricHeader}>
        <Icon name={icon} size={24} color={color} />
        <Text style={styles.metricTitle}>{title}</Text>
      </View>
      <Text style={styles.metricValue}>{value}</Text>
      {subtitle && <Text style={styles.metricSubtitle}>{subtitle}</Text>}
    </View>
  );

  const ServerStatusCard = ({server}) => (
    <View style={styles.serverCard}>
      <View style={styles.serverHeader}>
        <View style={styles.serverInfo}>
          <Text style={styles.serverName}>{server.name}</Text>
          <Text style={styles.serverType}>{server.server_type_display}</Text>
          <Text style={styles.serverIP}>{server.ip_address}</Text>
        </View>
        <View style={[styles.statusIndicator, {backgroundColor: getStatusColor(server.last_status)}]} />
      </View>
      
      <View style={styles.metricsRow}>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>CPU</Text>
          <Text style={styles.metricValue}>{server.last_cpu_percent}%</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>RAM</Text>
          <Text style={styles.metricValue}>{server.last_ram_percent}%</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Latency</Text>
          <Text style={styles.metricValue}>{server.last_latency_ms}ms</Text>
        </View>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading dashboard...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <Text style={styles.headerSubtitle}>Server Monitoring Overview</Text>
      </View>

      {dashboardData && (
        <View style={styles.metricsSection}>
          <MetricCard
            title="Total Servers"
            value={dashboardData.servers?.total || 0}
            subtitle={`${dashboardData.servers?.online || 0} online`}
            icon="dns"
            color="#2196F3"
          />
          <MetricCard
            title="Network Devices"
            value={dashboardData.network_devices?.total || 0}
            subtitle={`${dashboardData.network_devices?.active || 0} active`}
            icon="router"
            color="#FF9800"
          />
          <MetricCard
            title="Recent Alerts"
            value={dashboardData.alerts?.recent_24h || 0}
            subtitle={`${dashboardData.alerts?.critical || 0} critical`}
            icon="notifications"
            color="#F44336"
          />
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Server Status</Text>
        {serverStatus.length > 0 ? (
          serverStatus.map((server) => (
            <ServerStatusCard key={server.id} server={server} />
          ))
        ) : (
          <Text style={styles.emptyText}>No servers configured</Text>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#2196F3',
    padding: 20,
    paddingTop: 40,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.8,
    marginTop: 4,
  },
  metricsSection: {
    flexDirection: 'row',
    padding: 15,
    gap: 10,
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  metricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricTitle: {
    fontSize: 12,
    color: '#666',
    marginLeft: 8,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  metricSubtitle: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  section: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  serverCard: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  serverHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  serverInfo: {
    flex: 1,
  },
  serverName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  serverType: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  serverIP: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginTop: 4,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic',
  },
});

export default Dashboard;
