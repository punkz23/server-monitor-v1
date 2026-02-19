import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import APIService from '../services/api';

const Servers = ({navigation}) => {
  const [servers, setServers] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      const response = await APIService.getServerStatus();
      setServers(response.servers || []);
    } catch (error) {
      console.log('Servers load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadServers();
    setRefreshing(false);
  };

  const getStatusColor = (status) => {
    return status === 'UP' ? '#4CAF50' : '#F44336';
  };

  const getStatusIcon = (status) => {
    return status === 'UP' ? 'check-circle' : 'error';
  };

  const ServerCard = ({server}) => (
    <TouchableOpacity
      style={styles.serverCard}
      onPress={() => navigation.navigate('ServerDetail', {serverId: server.id})}>
      <View style={styles.serverHeader}>
        <View style={styles.serverInfo}>
          <Text style={styles.serverName}>{server.name}</Text>
          <Text style={styles.serverType}>{server.server_type_display}</Text>
          <Text style={styles.serverIP}>{server.ip_address}</Text>
        </View>
        <View style={styles.statusContainer}>
          <Icon 
            name={getStatusIcon(server.last_status)} 
            size={24} 
            color={getStatusColor(server.last_status)} 
          />
        </View>
      </View>
      
      <View style={styles.metricsContainer}>
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
      
      <View style={styles.footer}>
        <Text style={styles.lastChecked}>
          Last checked: {new Date(server.last_checked).toLocaleString()}
        </Text>
        <Icon name="chevron-right" size={20} color="#ccc" />
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Loading servers...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Servers</Text>
        <Text style={styles.headerSubtitle}>{servers.length} servers configured</Text>
      </View>
      
      <FlatList
        data={servers}
        renderItem={({item}) => <ServerCard server={item} />}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="dns" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No servers configured</Text>
            <Text style={styles.emptySubtext}>
              Add servers through the web interface to see them here
            </Text>
          </View>
        }
      />
    </View>
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
  loadingText: {
    marginTop: 10,
    color: '#666',
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
  listContainer: {
    padding: 15,
  },
  serverCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
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
  statusContainer: {
    alignItems: 'center',
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    backgroundColor: '#f8f9fa',
    padding: 10,
    borderRadius: 6,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lastChecked: {
    fontSize: 11,
    color: '#888',
    flex: 1,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginTop: 10,
    fontWeight: '500',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 5,
    textAlign: 'center',
  },
});

export default Servers;
