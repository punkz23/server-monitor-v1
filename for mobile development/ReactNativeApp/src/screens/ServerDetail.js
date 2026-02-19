import React, {useEffect, useState, useLayoutEffect} from 'react';
import {View, Text, StyleSheet, ScrollView, RefreshControl, ActivityIndicator} from 'react-native';
import APIService from '../services/api';

const InfoRow = ({label, value}) => (
  <View style={styles.infoRow}>
    <Text style={styles.infoLabel}>{label}</Text>
    <Text style={styles.infoValue}>{value ?? '—'}</Text>
  </View>
);

const ServerDetail = ({route, navigation}) => {
  const {serverId} = route.params;
  const [detail, setDetail] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useLayoutEffect(() => {
    navigation.setOptions({title: `Server #${serverId}`});
  }, [navigation, serverId]);

  useEffect(() => {
    loadData();
  }, [serverId]);

  const loadData = async () => {
    try {
      const [detailResp, metricsResp] = await Promise.all([
        APIService.getServerDetail(serverId),
        APIService.getServerMetrics(serverId, '24h'),
      ]);
      setDetail(detailResp);
      setMetrics(metricsResp);
    } catch (e) {
      console.log('Failed to load server detail:', e);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={styles.centered}> 
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Loading server details...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      {detail && (
        <View style={styles.card}>
          <Text style={styles.title}>{detail.name}</Text>
          <Text style={styles.subtitle}>{detail.server_type_display}</Text>

          <InfoRow label="IP Address" value={detail.ip_address} />
          <InfoRow label="Status" value={detail.last_status_display || detail.last_status} />
          <InfoRow label="CPU" value={`${detail.last_cpu_percent ?? '—'}%`} />
          <InfoRow label="RAM" value={`${detail.last_ram_percent ?? '—'}%`} />
          <InfoRow label="Latency" value={`${detail.last_latency_ms ?? '—'} ms`} />
          <InfoRow label="Last Checked" value={detail.last_checked ? new Date(detail.last_checked).toLocaleString() : '—'} />
        </View>
      )}

      {metrics && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Recent Metrics</Text>
          <Text style={styles.placeholder}>
            Metrics chart placeholder. Integrate react-native-chart-kit with metrics data when ready.
          </Text>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#f5f5f5'},
  centered: {flex: 1, justifyContent: 'center', alignItems: 'center'},
  loadingText: {marginTop: 8, color: '#666'},
  card: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {fontSize: 22, fontWeight: 'bold', color: '#333'},
  subtitle: {fontSize: 14, color: '#666', marginBottom: 12},
  sectionTitle: {fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 8},
  infoRow: {flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6},
  infoLabel: {color: '#666'},
  infoValue: {color: '#333', fontWeight: '600'},
  placeholder: {color: '#777', fontStyle: 'italic'},
});

export default ServerDetail;
