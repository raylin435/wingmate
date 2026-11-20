// Small localStorage helpers so the Date page can render a booking made on the Matches page.
// The API has no GET-booking route, so the booking object travels via storage + query string.

import type { Booking } from "./api";

export type StoredBooking = {
  booking: Booking;
  run_id: string;
  persona_id: string;
  candidate_id: string;
  partner_alias?: string;
  partner_first_name?: string;
  my_first_name?: string;
};

const bookingKey = (id: string) => `wingmate.booking.${id}`;
const LAST_BOOKING = "wingmate.lastBooking";

export function saveBooking(b: StoredBooking) {
  try {
    localStorage.setItem(bookingKey(b.booking.id), JSON.stringify(b));
    localStorage.setItem(LAST_BOOKING, b.booking.id);
  } catch {
    // ignore
  }
}

export function loadBooking(id: string): StoredBooking | null {
  try {
    const raw = localStorage.getItem(bookingKey(id));
    return raw ? (JSON.parse(raw) as StoredBooking) : null;
  } catch {
    return null;
  }
}

export function lastBookingId(): string | null {
  try {
    return localStorage.getItem(LAST_BOOKING);
  } catch {
    return null;
  }
}
