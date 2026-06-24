interface SearchBarProps {
  value: string
  onChange: (value: string) => void
}

export default function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <input
      type="search"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder="レシピ名・食材名で検索"
      style={{
        width: '100%',
        padding: '0.6rem 0.8rem',
        fontSize: '1rem',
        boxSizing: 'border-box',
        border: '1px solid #ccc',
        borderRadius: '6px'
      }}
    />
  )
}
