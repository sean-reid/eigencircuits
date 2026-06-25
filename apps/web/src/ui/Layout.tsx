import { useEffect, useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';

export function Layout() {
  const [dark, setDark] = useState(() => localStorage.getItem('ec-dark') === '1');
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('ec-dark', dark ? '1' : '0');
  }, [dark]);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const value = query.trim();
    if (!value) return;
    const id = value.replace(/^arxiv:/i, '');
    if (/^\d{4}\.\d{4,5}(v\d+)?$/.test(id)) navigate(`/abs/${id}`);
    else navigate(`/search?q=${encodeURIComponent(value)}`);
  };

  return (
    <div className="site">
      <header className="masthead">
        <Link to="/" className="wordmark">
          eigencircuits
        </Link>
        <form className="search" role="search" onSubmit={onSearch}>
          <input
            type="search"
            className="search-input"
            placeholder="Search title, author, abstract, or arXiv ID"
            aria-label="Search papers"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            spellCheck={false}
            autoComplete="off"
          />
          <button className="search-btn" type="submit">
            Search
          </button>
        </form>
        <nav className="masthead-links">
          <Link to="/about">About</Link>
          <button
            className="dark-toggle"
            onClick={() => setDark((d) => !d)}
            aria-label="Toggle dark mode"
            title="Toggle dark mode"
          >
            {dark ? '☀' : '☾'}
          </button>
        </nav>
      </header>

      <main className="content">
        <Outlet />
      </main>

      <footer className="footer">
        <nav className="footer-links">
          <Link to="/about">About</Link>
        </nav>
        <p className="footer-note">
          eigencircuits is a parody. Every paper here is machine-generated and mathematically
          meaningless; it is not affiliated with arXiv or Cornell University.
        </p>
      </footer>
    </div>
  );
}
