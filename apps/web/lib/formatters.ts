export const safeToFixed = (value: any, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0.' + '0'.repeat(decimals);
  }
  return Number(value).toFixed(decimals);
};

export const formatCurrency = (value: any): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return '$0.00';
  }
  return `$${Number(value).toFixed(2)}`;
};

export const formatPercent = (value: any, decimals: number = 1): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0.0%';
  }
  return `${Number(value).toFixed(decimals)}%`;
};
