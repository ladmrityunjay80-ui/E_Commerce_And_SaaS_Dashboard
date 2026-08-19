import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the login page when not authenticated', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
  });
});
