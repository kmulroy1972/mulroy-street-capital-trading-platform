const MSC_API_BASE = 'https://mulroystreetcap.com/api';

export async function getAccount() {
  const res = await fetch(`${MSC_API_BASE}/account`);
  if (!res.ok) throw new Error('Failed to fetch account');
  return res.json();
}

export async function getPositions() {
  const res = await fetch(`${MSC_API_BASE}/positions`);
  if (!res.ok) throw new Error('Failed to fetch positions');
  return res.json();
}

export async function getOrders(limit = 25) {
  const res = await fetch(`${MSC_API_BASE}/orders?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch orders');
  return res.json();
}

export async function getMarketClock() {
  const res = await fetch(`${MSC_API_BASE}/clock`);
  if (!res.ok) throw new Error('Failed to fetch market clock');
  return res.json();
}

export async function getHealth() {
  const res = await fetch('https://mulroystreetcap.com/health');
  if (!res.ok) throw new Error('API health check failed');
  return res.json();
}