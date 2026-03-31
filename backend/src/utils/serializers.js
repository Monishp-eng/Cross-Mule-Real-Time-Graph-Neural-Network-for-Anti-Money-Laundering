export function toPlainId(doc) {
  if (!doc) return null;
  return typeof doc.toObject === 'function' ? doc.toObject() : doc;
}

export function sortByTimestampDesc(items) {
  return [...items].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

export function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}
