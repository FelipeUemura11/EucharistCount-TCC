import { Component, type ErrorInfo, type ReactNode } from 'react';
import { TriangleAlert } from 'lucide-react';

interface Props { children: ReactNode }
interface State { hasError: boolean }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center p-8 text-center">
          <div>
            <TriangleAlert className="mx-auto mb-4 h-12 w-12 text-text-dark" />
            <h2 className="text-xl font-bold text-text-dark">Algo deu errado</h2>
            <p className="mt-2 text-sm text-text-muted">Tente recarregar a página.</p>
            <button
              type="button"
              className="mt-4 rounded-lg bg-secondary px-4 py-2 text-sm font-bold text-white"
              onClick={() => this.setState({ hasError: false })}
            >
              Tentar novamente
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
