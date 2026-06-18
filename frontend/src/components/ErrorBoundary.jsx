import React from 'react';
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
    this.setState({ errorInfo });
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 bg-bg-app text-status-bearish h-screen overflow-auto">
          <h2 className="text-2xl font-bold mb-4">React App Crashed</h2>
          <div className="bg-bg-elevated p-4 rounded mb-4 font-mono text-sm whitespace-pre-wrap">
            {this.state.error && this.state.error.toString()}
          </div>
          <div className="bg-bg-elevated p-4 rounded font-mono text-xs whitespace-pre-wrap opacity-80">
            {this.state.errorInfo && this.state.errorInfo.componentStack}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}