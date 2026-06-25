import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Layout } from './ui/Layout';

// Route-level code splitting: the archive landing stays lean, while KaTeX (used
// by the rendered views) and the PDF engine wrapper load only when needed.
const ArchivePage = lazy(() =>
  import('./pages/ArchivePage').then((m) => ({ default: m.ArchivePage })),
);
const ListPage = lazy(() => import('./pages/ListPage').then((m) => ({ default: m.ListPage })));
const SearchPage = lazy(() =>
  import('./pages/SearchPage').then((m) => ({ default: m.SearchPage })),
);
const AboutPage = lazy(() => import('./pages/AboutPage').then((m) => ({ default: m.AboutPage })));
const AbsPage = lazy(() => import('./pages/AbsPage').then((m) => ({ default: m.AbsPage })));
const HtmlPage = lazy(() => import('./pages/HtmlPage').then((m) => ({ default: m.HtmlPage })));
const PdfPage = lazy(() => import('./pages/PdfPage').then((m) => ({ default: m.PdfPage })));
const NotFound = lazy(() => import('./pages/NotFound').then((m) => ({ default: m.NotFound })));

export function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<p className="status">Loading…</p>}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<ArchivePage />} />
            <Route path="/archive/math" element={<ArchivePage />} />
            <Route path="/list/:cat/:period" element={<ListPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/abs/:id" element={<AbsPage />} />
            <Route path="/html/:id" element={<HtmlPage />} />
            <Route path="/pdf/:id" element={<PdfPage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
