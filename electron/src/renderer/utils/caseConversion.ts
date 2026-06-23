/**
 * Case Conversion Utilities
 *
 * The Python/FastAPI backend serializes JSON using snake_case (the Python
 * convention). The React/TypeScript frontend uses camelCase (the JS/TS
 * convention). Rather than scatter ad-hoc field renames across every thunk
 * and component, all backend traffic is normalized at this single boundary.
 *
 * - Outgoing requests: camelToSnake() before sending to the API
 * - Incoming responses: snakeToCamel() right after receiving from the API
 *
 * Both functions are deep and array-aware, so nested objects (file trees,
 * stats distributions, etc.) are converted recursively.
 */

type JSONValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | JSONValue[]
  | { [key: string]: JSONValue };

function snakeToCamelKey(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_, char: string) => char.toUpperCase());
}

function camelToSnakeKey(key: string): string {
  return key.replace(/[A-Z]/g, (char) => `_${char.toLowerCase()}`);
}

function transformKeys<T extends JSONValue>(
  value: T,
  keyFn: (key: string) => string
): T {
  if (Array.isArray(value)) {
    return value.map((item) => transformKeys(item, keyFn)) as unknown as T;
  }
  if (value !== null && typeof value === 'object') {
    const result: Record<string, JSONValue> = {};
    for (const [key, val] of Object.entries(value as Record<string, JSONValue>)) {
      result[keyFn(key)] = transformKeys(val, keyFn);
    }
    return result as T;
  }
  return value;
}

/** Recursively converts all object keys from snake_case to camelCase. */
export function snakeToCamel<T extends JSONValue>(value: T): T {
  return transformKeys(value, snakeToCamelKey);
}

/** Recursively converts all object keys from camelCase to snake_case. */
export function camelToSnake<T extends JSONValue>(value: T): T {
  return transformKeys(value, camelToSnakeKey);
}
