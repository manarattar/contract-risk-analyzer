import PropTypes from 'prop-types';
import { Component } from "react";

/** If something on the page breaks, say so plainly instead of leaving a blank screen. */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Contract Risk Analyzer crashed:", error, info?.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="flex min-h-screen items-center justify-center bg-desk px-4">
        <div className="w-full max-w-md rounded-[4px] border border-rule bg-sheet p-6">
          <h1 className="font-serif text-[22px] font-semibold text-ink">Something went wrong</h1>
          <p className="mt-2 text-[14px] leading-relaxed text-ink-2">
            The page hit an error and stopped. Reload it and run the analysis again; the sample contract
            takes about a minute.
          </p>
          <p className="num mt-3 break-words rounded-[3px] bg-desk px-3 py-2 text-[12px] text-ink-3">
            {String(this.state.error.message || this.state.error)}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 rounded-[3px] bg-ink px-4 py-2 text-[14px] font-medium text-sheet hover:opacity-90"
          >
            Reload the page
          </button>
        </div>
      </div>
    );
  }
}

ErrorBoundary.propTypes = { children: PropTypes.node };
