import type { PaperModel } from './paperModel';

export interface SubjectCount {
  code: string;
  name: string;
  count: number;
}

export interface ArchiveResponse {
  archive: string;
  subjects: SubjectCount[];
  total: number;
  recent_dates: string[];
}

export interface CrossList {
  code: string;
  name: string;
}

export interface ListEntry {
  id: string;
  date: string;
  title: string;
  authors: string[];
  comments: string;
  primary: string;
  primary_name: string;
  crosslist: CrossList[];
  abstract?: string;
}

export interface ListResponse {
  cat: string;
  name: string;
  period: string;
  total: number;
  skip: number;
  show: number;
  recent_dates: string[];
  entries: ListEntry[];
}

export interface SearchResponse {
  query: string;
  cat: string;
  total: number;
  skip: number;
  show: number;
  entries: ListEntry[];
}

export interface SubmissionVersion {
  version: number;
  datetime: string;
  size_kb: number;
}

export interface AbsResponse {
  id: string;
  date: string;
  comments: string;
  submitter: string;
  submission: SubmissionVersion[];
  msc_primary: string;
  msc_secondary: string[];
  primary: string;
  primary_name: string;
  crosslist: CrossList[];
  model: PaperModel;
  tex: string;
}
