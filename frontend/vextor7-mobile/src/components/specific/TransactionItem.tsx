import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { theme } from '@/styles/theme';
import { Typography } from '@/components/common/Typography';
import { Icon } from '@/components/common/Icon';
import { Transaction, TransactionStatus, TransactionType } from '@/types/wallet';
import { formatDate } from '@/utils/helpers';

interface TransactionItemProps {
  transaction: Transaction;
  onPress: (tx: Transaction) => void;
}

export const TransactionItem: React.FC<TransactionItemProps> = ({ transaction, onPress }) => {
  const isReceived = transaction.type === TransactionType.RECEIVE;
  const isFailed = transaction.status === TransactionStatus.FAILED;

  const getIcon = () => {
    if (isFailed) return 'alert-circle';
    switch (transaction.type) {
      case TransactionType.SEND: return 'arrow-up-right';
      case TransactionType.RECEIVE: return 'arrow-down-left';
      case TransactionType.SWAP: return 'repeat';
      case TransactionType.DEPOSIT: return 'download';
      case TransactionType.WITHDRAWAL: return 'upload';
      default: return 'activity';
    }
  };

  const getColor = () => {
    if (isFailed) return theme.colors.error;
    if (isReceived) return theme.colors.success;
    return theme.colors.textPrimary;
  };

  const getAmountPrefix = () => {
    if (isReceived) return '+';
    return '-';
  };

  return (
    <TouchableOpacity style={styles.container} onPress={() => onPress(transaction)}>
      <View style={[styles.iconContainer, { backgroundColor: theme.colors.backgroundTertiary }]}>
        <Icon name={getIcon()} size={20} color={getColor()} />
      </View>

      <View style={styles.details}>
        <Typography variant="body" weight="medium">
          {transaction.type === TransactionType.SWAP ? 'Swap' : 
           transaction.type === TransactionType.SEND ? 'Sent' : 'Received'}
        </Typography>
        <Typography variant="caption" color={theme.colors.textSecondary}>
          {formatDate(transaction.timestamp)} • {transaction.status}
        </Typography>
      </View>

      <View style={styles.amount}>
        <Typography variant="body" weight="bold" color={getColor()}>
          {getAmountPrefix()} {transaction.amountFormatted} {transaction.symbol}
        </Typography>
        <Typography variant="caption" color={theme.colors.textSecondary}>
           {/* USD value logic could go here */}
        </Typography>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing.m,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: theme.spacing.m,
  },
  details: {
    flex: 1,
  },
  amount: {
    alignItems: 'flex-end',
  },
});