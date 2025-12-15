import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CurrencyConverter from '../CurrencyConverter';

// Mock global.fetch pour tous les tests
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('CurrencyConverter Component', () => {
  const mockRatesResponse = {
    conversion_rates: {
      USD: 1,
      EUR: 0.85,
      MAD: 10.0,
      GBP: 0.73,
      JPY: 110.0
    },
    time_last_update_utc: 'Mon, 08 Dec 2025 00:00:00 +0000'
  };

  beforeEach(() => {
    mockFetch.mockClear();
    // Réinitialiser localStorage si utilisé
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders the component', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRatesResponse
    });

    render(<CurrencyConverter />);
    expect(screen.getByText(/Loading exchange rates/i)).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    // Ne pas résoudre la promesse pour garder l'état de chargement
    mockFetch.mockImplementationOnce(() => new Promise(() => {}));
    
    render(<CurrencyConverter />);
    expect(screen.getByText(/Loading exchange rates/i)).toBeInTheDocument();
  });

  it('fetches and displays exchange rates', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRatesResponse
    });

    render(<CurrencyConverter />);

    await waitFor(() => {
      const selects = screen.getAllByRole('combobox');
      expect(selects).toHaveLength(2);
    });

    const selects = screen.getAllByRole('combobox');
    expect(selects[0]).toHaveValue('USD');
    expect(selects[1]).toHaveValue('EUR');
  });

  it('converts currency correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRatesResponse
    });

    render(<CurrencyConverter />);

    await waitFor(() => {
      expect(screen.getAllByRole('combobox')).toHaveLength(2);
    });

    const input = screen.getByPlaceholderText(/Enter amount/i);
    await userEvent.clear(input);
    await userEvent.type(input, '100');

    await waitFor(() => {
      expect(screen.getByText(/100 USD/)).toBeInTheDocument();
      expect(screen.getByText(/85.0000 EUR/)).toBeInTheDocument();
    });
  });

  it('switches currencies when button is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRatesResponse
    });

    render(<CurrencyConverter />);

    await waitFor(() => {
      expect(screen.getAllByRole('combobox')).toHaveLength(2);
    });

    const selects = screen.getAllByRole('combobox');
    const initialFrom = selects[0].value;
    const initialTo = selects[1].value;

    const switchButton = screen.getByRole('button', { name: /⇄/i });
    fireEvent.click(switchButton);

    await waitFor(() => {
      const updatedSelects = screen.getAllByRole('combobox');
      expect(updatedSelects[0].value).toBe(initialTo);
      expect(updatedSelects[1].value).toBe(initialFrom);
    });
  });

  it('handles API errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'));
    
    render(<CurrencyConverter />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/i)).toBeInTheDocument();
    });
  });

  it('handles non-numeric input gracefully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRatesResponse
    });

    render(<CurrencyConverter />);

    await waitFor(() => {
      expect(screen.getAllByRole('combobox')).toHaveLength(2);
    });

    const input = screen.getByPlaceholderText(/Enter amount/i);
    await userEvent.clear(input);
    await userEvent.type(input, 'abc');

    // Le champ doit être vide ou gérer la conversion
    expect(input.value).toBe('');
  });
});