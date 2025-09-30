const STORAGE_KEY = 'te_client_id';

export function getClientId(): string {
  if (typeof window === 'undefined') {
    return 'server';
  }
  let existing = window.localStorage.getItem(STORAGE_KEY);
  if (!existing) {
    existing = crypto.randomUUID();
    window.localStorage.setItem(STORAGE_KEY, existing);
  }
  return existing;
}
