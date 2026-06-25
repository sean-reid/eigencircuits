import { Link } from 'react-router-dom';

export function NotFound() {
  return (
    <p className="status">
      Page not found. <Link to="/">Return to the archive.</Link>
    </p>
  );
}
