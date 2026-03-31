import { AlertTriangle, RefreshCw, XCircle } from 'lucide-react';
import { Button } from './button';

interface ErrorMessageProps {
  error: Error | string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorMessage({ error, onRetry, className = '' }: ErrorMessageProps) {
  const errorMessage = typeof error === 'string' ? error : error.message;

  return (
    <div className={`flex flex-col items-center justify-center text-center ${className}`}>
      <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20 mb-4">
        <AlertTriangle className="w-8 h-8 text-red-400" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">Something went wrong</h3>
      <p className="text-sm text-slate-400 mb-4 max-w-md">{errorMessage}</p>
      {onRetry && (
        <Button
          onClick={onRetry}
          className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
}

interface ErrorCardProps {
  error: Error | string;
  onRetry?: () => void;
}

export function ErrorCard({ error, onRetry }: ErrorCardProps) {
  return (
    <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-red-500/20 p-12">
      <ErrorMessage error={error} onRetry={onRetry} />
    </div>
  );
}

interface ErrorBannerProps {
  error: Error | string;
  onDismiss?: () => void;
}

export function ErrorBanner({ error, onDismiss }: ErrorBannerProps) {
  const errorMessage = typeof error === 'string' ? error : error.message;

  return (
    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-red-400 mb-1">Error</h4>
          <p className="text-sm text-slate-300">{errorMessage}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-slate-300 transition-colors"
          >
            <XCircle className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
}

interface NetworkErrorProps {
  onRetry?: () => void;
}

export function NetworkError({ onRetry }: NetworkErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <div className="p-6 rounded-full bg-orange-500/10 border border-orange-500/20 mb-6">
        <AlertTriangle className="w-12 h-12 text-orange-400" />
      </div>
      <h3 className="text-2xl font-bold text-white mb-2">Network Connection Error</h3>
      <p className="text-slate-400 mb-6 max-w-md text-center">
        Unable to connect to the server. Please check your internet connection and try again.
      </p>
      {onRetry && (
        <Button
          onClick={onRetry}
          className="bg-cyan-500 hover:bg-cyan-600 text-white"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry Connection
        </Button>
      )}
    </div>
  );
}
