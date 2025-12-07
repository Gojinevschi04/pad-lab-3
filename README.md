##### _"Seat availability, booking, validation"_

# Ticketing Service
The Ticketing Service is responsible for managing bus ticket reservations,
confirmations, cancellations, validations, and ticket file generation
within a distributed transport system.

## Functionalities
### Ticket Reservation
Users can reserve a seat on a specific trip by submitting the trip ID and seat number.
- The reservation holds the seat for a limited time (e.g., 15 minutes), during which the user must complete the payment.
- Seat availability is validated via the Trip Service.
- Available seats can be requested via a dedicated endpoint.

### Ticket Confirmation (Post-payment)
- After a successful payment, the Payment Service notifies the Ticketing Service.
The ticket status is updated to paid.
- A background task generates a PDF version of the ticket and stores it in MinIO.
- The PDF includes a QR code for fast validation.

### Ticket Expiration
- If a ticket is not paid within the reservation window, its status is automatically updated to expired.
This is managed via Celery scheduled tasks.
- Expired tickets release the reserved seat through the Trip Service.

### Ticket Cancellation
- Users can cancel tickets before or after payment, depending on business rules.
#### On cancellation:
- The ticket status is set to cancelled.
- The reserved seat is released via the Trip Service.
- If the ticket was already paid, a refund may be triggered through the Payment Service.

### Ticket Validation
- Tickets can be validated before trip departure.
- Only tickets with status paid and not expired can be validated.
- Validation marks the ticket as used, preventing reuse.
- Validation is performed via a dedicated endpoint, typically triggered by scanning the ticket’s QR code.

### Ticket Download
- Paid tickets can be downloaded as PDF files stored in MinIO.
- Downloads are available only to the authenticated ticket owner.
- The system also sends the ticket via email after payment confirmation.

### Ticket Search
Tickets are indexed in Elasticsearch.
Search supports filtering by:
- trip name
- seat number
- ticket status
- user information

### Trip Calendar Export (ICS)
- Users can download an .ics file containing calendar events for upcoming paid trips.
- Each event includes trip name, departure time, location, seat number, and ticket ID.
Useful for importing into personal calendars.

### Promo Code Management
Admins can create and manage promo codes with:
- code string
- discount value (fixed or percentage)
- validity period
- usage limits

Users can apply promo codes during ticket reservation.
The system validates the code and applies the discount to the final ticket price.

### View Ticket History
Users can view a list of their past tickets, including:
cancelled, expired, and completed trips
Each entry includes trip details, seat, status, and timestamps.

### Notifications
The system sends email notifications to users for:
ticket confirmation (with PDF attachment)
upcoming trip reminders (e.g., 24h or 1h before departure)
All notifications are handled as background Celery tasks.

### Admin Statistics and Monitoring
Admins can access reports and aggregated data, including:
- number of tickets sold
- most active routes
- promo code usage
- seat occupancy rates

These statistics can be exposed via API endpoints or admin dashboards.


