// frontend/src/components/PlaceholderPage.tsx
interface PlaceholderProps {
  title: string;
}

const PlaceholderPage = ({ title }: PlaceholderProps) => {
  return (
    <div className="placeholder-page">
      <h2>{title}</h2>
      <p>Coming soon...</p>
    </div>
  );
};

export default PlaceholderPage;