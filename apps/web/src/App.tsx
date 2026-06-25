import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AbsPage } from './pages/AbsPage';
import { AboutPage } from './pages/AboutPage';
import { ArchivePage } from './pages/ArchivePage';
import { HtmlPage } from './pages/HtmlPage';
import { ListPage } from './pages/ListPage';
import { NotFound } from './pages/NotFound';
import { SearchPage } from './pages/SearchPage';
import { Layout } from './ui/Layout';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<ArchivePage />} />
          <Route path="/archive/math" element={<ArchivePage />} />
          <Route path="/list/:cat/:period" element={<ListPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/abs/:id" element={<AbsPage />} />
          <Route path="/html/:id" element={<HtmlPage />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
