/**
 * Minimal TypeScript wrapper around the SwiftLaTeX pdfTeX Web Worker.
 *
 * The worker (`/swiftlatexpdftex.js`) and its WebAssembly module
 * (`/swiftlatexpdftex.wasm`) are vendored under `public/`; TeX packages are
 * fetched on demand from the SwiftLaTeX TeX Live mirror. This is a hand-written
 * port of SwiftLaTeX's PdfTeXEngine.js with an absolute worker URL (so it
 * resolves from any SPA route) and proper types.
 */

const ENGINE_URL = '/swiftlatexpdftex.js';

export enum EngineStatus {
  Init = 1,
  Ready = 2,
  Busy = 3,
  Error = 4,
}

export interface CompileResult {
  /** PDF bytes when `status === 0`, otherwise undefined. */
  pdf?: Uint8Array;
  /** pdfTeX exit status; 0 means success. */
  status: number;
  /** Full compiler log. */
  log: string;
}

export class PdfTeXEngine {
  private worker: Worker | undefined;
  private status: EngineStatus = EngineStatus.Init;

  isReady(): boolean {
    return this.status === EngineStatus.Ready;
  }

  async loadEngine(): Promise<void> {
    if (this.worker !== undefined) {
      throw new Error('PdfTeXEngine is already loaded');
    }
    this.status = EngineStatus.Init;
    const worker = new Worker(ENGINE_URL);
    try {
      await new Promise<void>((resolve, reject) => {
        worker.onmessage = (ev: MessageEvent) => {
          const data = ev.data as { result?: string };
          if (data.result === 'ok') {
            this.status = EngineStatus.Ready;
            resolve();
          } else {
            this.status = EngineStatus.Error;
            reject(new Error('Failed to start the pdfTeX worker'));
          }
        };
        worker.onerror = () => {
          this.status = EngineStatus.Error;
          reject(new Error('Failed to load the pdfTeX worker'));
        };
      });
    } catch (err) {
      worker.terminate();
      throw err;
    }
    worker.onmessage = null;
    worker.onerror = null;
    this.worker = worker;
  }

  private checkReady(): void {
    if (!this.isReady()) {
      throw new Error('pdfTeX engine is not ready');
    }
  }

  setEngineMainFile(filename: string): void {
    this.checkReady();
    this.worker?.postMessage({ cmd: 'setmainfile', url: filename });
  }

  writeMemFSFile(filename: string, src: string | Uint8Array): void {
    this.checkReady();
    this.worker?.postMessage({ cmd: 'writefile', url: filename, src });
  }

  makeMemFSFolder(folder: string): void {
    this.checkReady();
    if (!folder || folder === '/') return;
    this.worker?.postMessage({ cmd: 'mkdir', url: folder });
  }

  setTexliveEndpoint(url: string): void {
    this.worker?.postMessage({ cmd: 'settexliveurl', url });
  }

  flushCache(): void {
    this.checkReady();
    this.worker?.postMessage({ cmd: 'flushcache' });
  }

  async compileLaTeX(): Promise<CompileResult> {
    this.checkReady();
    this.status = EngineStatus.Busy;
    const worker = this.worker;
    const result = await new Promise<CompileResult>((resolve) => {
      if (!worker) {
        resolve({ status: -1, log: 'pdfTeX worker is not available' });
        return;
      }
      worker.onmessage = (ev: MessageEvent) => {
        const data = ev.data as {
          cmd?: string;
          result?: string;
          log?: string;
          status?: number;
          pdf?: ArrayBuffer;
        };
        if (data.cmd !== 'compile') return;
        this.status = EngineStatus.Ready;
        const report: CompileResult = {
          status: data.status ?? -254,
          log: data.log ?? 'No log',
        };
        if (data.result === 'ok' && data.pdf) {
          report.pdf = new Uint8Array(data.pdf);
        }
        resolve(report);
      };
      worker.postMessage({ cmd: 'compilelatex' });
    });
    if (this.worker) this.worker.onmessage = null;
    return result;
  }

  close(): void {
    this.worker?.postMessage({ cmd: 'grace' });
    this.worker = undefined;
    this.status = EngineStatus.Init;
  }
}
