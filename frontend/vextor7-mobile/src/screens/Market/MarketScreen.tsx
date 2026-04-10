import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, Image, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Typography } from '@/components/common/Typography';
import { Icon } from '@/components/common/Icon';
import { Input } from '@/components/common/Input';
import { theme } from '@/styles/theme';
import { marketApi } from '@/api/services/marketApi';
import { formatCurrency } from '@/utils/helpers';
import { useDebounce } from '@/hooks/useDebounce';
import { MarketCoin } from '@/types/api';

export default function MarketScreen() {
  const [coins, setCoins] = useState<MarketCoin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 500);

  useEffect(() => {
    fetchMarketData();
  }, []);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      // In production, implement search parameter if the API supports it
      const data = await marketApi.getCoins(1);
      setCoins(data.items || data); // Adjust based on your API response structure
    } catch (error) {
      console.error('Failed to fetch market data', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCoins = coins.filter(c => 
    c.name.toLowerCase().includes(debouncedSearch.toLowerCase()) || 
    c.symbol.toLowerCase().includes(debouncedSearch.toLowerCase())
  );

  const renderCoin = ({ item }: { item: MarketCoin }) => {
    const isPositive = item.price_change_percentage_24h >= 0;
    
    return (
      <TouchableOpacity style={styles.coinRow} activeOpacity={0.7}>
        <View style={styles.coinLeft}>
          <Image source={{ uri: item.image }} style={styles.coinImage} />
          <View>
            <Typography variant="body" weight="bold">{item.name}</Typography>
            <Typography variant="caption" color={theme.colors.textSecondary} style={{ textTransform: 'uppercase' }}>
              {item.symbol}
            </Typography>
          </View>
        </View>

        <View style={styles.coinRight}>
          <Typography variant="body" weight="bold">{formatCurrency(item.current_price)}</Typography>
          <View style={styles.changeBadge}>
            <Icon 
              name={isPositive ? 'trending-up' : 'trending-down'} 
              size={12} 
              color={isPositive ? theme.colors.success : theme.colors.error} 
            />
            <Typography 
              variant="caption" 
              color={isPositive ? theme.colors.success : theme.colors.error}
              style={{ marginLeft: 4 }}
            >
              {Math.abs(item.price_change_percentage_24h).toFixed(2)}%
            </Typography>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaViewWrapper>
      <Header title="Market" showBack={false} rightIcon="bell" onRightPress={() => console.log('Alerts')} />
      
      <View style={styles.searchContainer}>
        <Input 
          placeholder="Search coins..." 
          leftIcon="search"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      ) : (
        <FlatList
          data={filteredCoins}
          keyExtractor={(item) => item.id}
          renderItem={renderCoin}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  searchContainer: { paddingHorizontal: theme.spacing.m, paddingTop: theme.spacing.m },
  listContent: { paddingHorizontal: theme.spacing.m, paddingBottom: theme.spacing.xxl },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  coinRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: theme.spacing.m, borderBottomWidth: 1, borderBottomColor: theme.colors.divider },
  coinLeft: { flexDirection: 'row', alignItems: 'center' },
  coinImage: { width: 40, height: 40, borderRadius: 20, marginRight: theme.spacing.m, backgroundColor: theme.colors.backgroundTertiary },
  coinRight: { alignItems: 'flex-end' },
  changeBadge: { flexDirection: 'row', alignItems: 'center', marginTop: 4 },
});