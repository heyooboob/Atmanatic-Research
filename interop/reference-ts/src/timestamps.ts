/** Shared RFC 3339 timestamp parsing, mirroring atmanatic_research/timestamps.py.
 * Every 0.1 wire timestamp MUST include an explicit UTC offset; naive
 * timestamps are rejected rather than silently assumed to be UTC.
 */

const RFC3339_PATTERN =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

export class TimestampError extends Error {}

/** Validate `value` as an offset-aware RFC 3339 timestamp or throw `TimestampError`. */
export function parseRfc3339(value: unknown, field: string): Date {
  if (typeof value !== "string" || value.trim() === "") {
    throw new TimestampError(`${field} must be a non-empty timestamp string`);
  }
  const text = value.trim();
  if (!RFC3339_PATTERN.test(text)) {
    throw new TimestampError(`${field} must include an explicit UTC offset`);
  }
  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) {
    throw new TimestampError(`${field} must be a valid RFC 3339 timestamp`);
  }
  return parsed;
}
