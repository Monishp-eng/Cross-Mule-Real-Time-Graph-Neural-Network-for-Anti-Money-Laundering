export const currency = (value = 0, currencyCode = "INR") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: currencyCode || "INR", maximumFractionDigits: 2 }).format(
    Number(value) || 0
  );

export const dateTime = (value) => {
  if (!value) return "-";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return String(value);
  return dt.toLocaleString();
};

export const toArray = (payload) => {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.transactions)) return payload.transactions;
  if (Array.isArray(payload?.alerts)) return payload.alerts;
  return [];
};

export const scoreToRisk = (score) => {
  const val = Number(score) || 0;
  if (val >= 0.75) return "High";
  if (val >= 0.4) return "Medium";
  return "Low";
};
