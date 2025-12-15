import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('App Component', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        conversion_rates: {
          USD: 1,
          EUR: 0.85,
          MAD: 10.0
        }
      })
    });
  });

  it('renders without crashing', () => {
    render(<App />);
    const appElement = document.querySelector('.App');
    expect(appElement).toBeInTheDocument();
  });

  it('renders CurrencyConverter component', async () => {
    render(<App />);
    
    // Attendre que le composant soit chargé
    const heading = await screen.findByText(
      /Currency Converter/i,
      {},
      { timeout: 2000 }
    );
    
    expect(heading).toBeInTheDocument();
  });

  it('has correct layout structure', () => {
    render(<App />);
    
    const mainContainer = screen.getByRole('main');
    expect(mainContainer).toBeInTheDocument();
    
    // Vérifier les classes CSS
    expect(mainContainer).toHaveClass('App');
  });
});