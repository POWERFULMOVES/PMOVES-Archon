import { render, screen } from '@testing-library/react';
import HomePage from '@/app/page';

describe('HomePage', () => {
  it('provides navigation to the ingestion dashboard', () => {
    render(<HomePage />);
    expect(
      screen.getByRole('link', { name: /ingestion dashboard/i })
    ).toBeInTheDocument();
  });
});
