"""Print a one-time password reset link for an operator to send by hand.

The HTTP forgot-password endpoint never prints this link. SMTP, when
configured, is the only automatic delivery.
"""

import sys


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("Usage: python -m tools.reset_link <email>", file=sys.stderr)
        return 2
    from server import issue_password_reset

    result = issue_password_reset(sys.argv[1].strip(), reveal=True)
    if result is None:
        print("No household account uses that email.", file=sys.stderr)
        return 1
    if result == "limited":
        print("Too many reset links for that account. Try again later.", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
