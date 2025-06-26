# Verification Flow Documentation

This document outlines the verification flow for user email and phone number verification in the ZeitWise application.

## Overview

The verification system allows users to verify their email addresses and phone numbers. It integrates with Supabase Auth for the actual verification process while maintaining a local copy of the verification status in our database.

## Verification Types

1. **Email Verification**
   - Users receive a verification link via email
   - Clicking the link marks the email as verified in Supabase
   - The local database is updated to reflect this status

2. **Phone Verification**
   - Users receive an OTP (One-Time Password) via SMS
   - They submit this OTP to verify their phone number
   - The system validates the OTP with Supabase and updates the local database

## API Endpoints

### 1. Check Verification Status

```http
GET /api/verification/status/{verification_type}
```

**Parameters:**
- `verification_type` (path): Either "email" or "phone"

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user-uuid-here",
    "type": "email",
    "is_verified": true,
    "verified_at": "2023-01-01T12:00:00Z",
    "contact": "user@example.com",
    "provider": "email"
  }
}
```

### 2. Resend Verification

```http
POST /api/verification/resend
```

**Request Body:**
```json
{
  "verification_type": "email",
  "redirect_url": "https://yourapp.com/verify-success"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Verification email sent",
    "contact": "user@example.com",
    "type": "email"
  }
}
```

### 3. Verify Phone with OTP

```http
POST /api/verification/verify-phone
```

**Request Body:**
```json
{
  "phone": "+1234567890",
  "token": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Phone number verified successfully",
    "user_id": "user-uuid-here",
    "phone": "+1234567890",
    "is_verified": true
  }
}
```

## Integration with Authentication Flow

1. **After Signup/Login**
   - Check verification status using `/verification/status/{type}`
   - If not verified, show appropriate UI to request verification
   - Allow users to resend verification if needed

2. **Email Verification**
   - User requests verification email
   - System sends email with verification link
   - Link points to a frontend route that calls the Supabase verification endpoint
   - Frontend updates UI based on verification result

3. **Phone Verification**
   - User requests phone verification
   - System sends OTP via SMS
   - User enters OTP in the app
   - App verifies OTP with the backend
   - UI updates based on verification result

## Error Handling

Common error responses include:

- `400 Bad Request`: Invalid verification type or missing parameters
- `401 Unauthorized`: User not authenticated
- `404 Not Found`: User not found
- `429 Too Many Requests`: Too many verification attempts

## Testing

### Test Cases

1. **Email Verification**
   - Register a new user with an email
   - Check verification status (should be false)
   - Request verification email
   - Click verification link
   - Check status again (should be true)

2. **Phone Verification**
   - Register a new user with a phone number
   - Request OTP
   - Submit valid OTP
   - Verify status is updated
   - Test with invalid OTP (should fail)

3. **Resend Verification**
   - Request verification email
   - Immediately request another (should respect rate limits)
   - Verify only one email is sent within the rate limit window

## Security Considerations

- Rate limiting is implemented to prevent abuse
- Verification links expire after a set period
- OTPs are single-use and expire after a short duration
- All verification endpoints require authentication
- Sensitive information is never returned in responses

## Dependencies

- Supabase Auth for verification services
- Local database for storing verification status
- Email/SMS services for sending verification codes

## Future Enhancements

1. Support for multiple verification methods
2. Webhook integration for real-time verification status updates
3. Customizable verification email/SMS templates
4. Support for 2FA (Two-Factor Authentication)
5. Rate limiting configuration options
