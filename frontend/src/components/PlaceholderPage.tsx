// frontend/src/components/PlaceholderPage.tsx
interface PlaceholderProps {
  title: string;
  description?: string; // Añade una descripción opcional
}

const PlaceholderPage = ({ title, description }: PlaceholderProps) => {
  return (
    <div className="placeholder-page">
      <h2>{title}</h2>
      {description && <p>{description}</p>} {/* Muestra la descripción si existe */}
      <p style={{ marginTop: '20px', fontStyle: 'italic', color: '#aaa' }}>
        (Contenido Próximamente...)
      </p>
    </div>
  );
};

export default PlaceholderPage;