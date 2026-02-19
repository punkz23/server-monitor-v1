import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import APIService from '../services/api';

const Alerts = ({navigation}) => {
  const [alerts, setAlerts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, critical, warning, info

  useEffect(() => {
    loadAlerts();
  }, [filter]);

  const loadAlerts = async () => {
    try {
      const params = {};
      if (filter !== 'all') {
        params.severity = filter.toUpperCase();
      }
      
      const response = await APIService.getAlerts(params);
      setAlerts(response.results || response || []);
    } catch (error) {
      console.log('Alerts load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadAlerts();
    setRefreshing(false);
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return '#F44336';
      case 'warning':
        return '#FF9800';
      case 'info':
        return '#2196F3';
      default:
        return '#666';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'notifications';
    }
  };

  const FilterButton = ({label, value, color}) => (
    <TouchableOpacity
      style={[
        styles.filterButton,
        filter === value && {backgroundColor: color, borderColor: color},
      ]}
      onPress={() => setFilter(value)}>
      <Text
        style={[
          styles.filterButtonText,
          filter === value && {color: '#fff'},
        ]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  const AlertCard = ({alert}) => (
    <View style={styles.alertCard}>
      <View style={styles.alertHeader}>
        <View style={styles.alertInfo}>
          <View style={[styles.severityIndicator, {backgroundColor: getSeverityColor(alert.severity)}]}>
            <Icon name={getSeverityIcon(alert.severity)} size={16} color="#fff" />
          </View>
          <Text style={styles.alertTitle}>{alert.title || 'Alert'}</Text>
        </View>
        <Text style={styles.alertSeverity}>{alert.severity}</Text>
      </View>
      
      <Text style={styles.alertMessage}>{alert.message}</Text>
      
      {alert.server && (
        <View style={styles.alertServer}>
          <Icon name="dns" size={14} color="#666" />
          <Text style={styles.alertServerText}>{alert.server}</Text>
        </View>
      )}
      
      <View style={styles.alertFooter}>
        <Text style={styles.alertTime}>
          {new Date(alert.created_at).toLocaleString()}
        </Text>
        {alert.resolved && (
          <View style={styles.resolvedBadge}>
            <Text style={styles.resolvedText}>Resolved</Text>
          </View>
        )}
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Loading alerts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Alerts</Text>
        <Text style={styles.headerSubtitle}>{alerts.length} alerts</Text>
      </View>
      
      <View style={styles.filterContainer}>
        <FilterButton label="All" value="all" color="#666" />
        <FilterButton label="Critical" value="critical" color="#F44336" />
        <FilterButton label="Warning" value="warning" color="#FF9800" />
        <FilterButton label="Info" value="info" color="#2196F3" />
      </View>
      
      <FlatList
        data={alerts}
        renderItem={({item}) => <AlertCard alert={item} />}
        keyExtractor={(item, index) => index.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="notifications-none" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No alerts found</Text>
            <Text style={styles.emptySubtext}>
              {filter === 'all' 
                ? 'No alerts have been generated' 
                : `No ${filter} alerts found`}
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
  filterContainer: {
    flexDirection: 'row',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  filterButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginHorizontal: 2,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  filterButtonText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  listContainer: {
    padding: 15,
  },
  alertCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#ddd',
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  severityIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  alertTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  alertSeverity: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
    textTransform: 'uppercase',
  },
  alertMessage: {
    fontSize: 14,
    color: '#555',
    marginBottom: 8,
    lineHeight: 20,
  },
  alertServer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertServerText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  alertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  alertTime: {
    fontSize: 11,
    color: '#888',
    flex: 1,
  },
  resolvedBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  resolvedText: {
    fontSize: 10,
    color: '#fff',
    fontWeight: 'bold',
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

export default Alerts;
