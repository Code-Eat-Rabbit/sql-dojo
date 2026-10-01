type Col = { name: string; type?: string }

export default function ResultTable({
  columns,
  rows,
}: {
  columns: Col[]
  rows: unknown[][]
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
            {columns.map((col, i) => (
              <th key={i} className="px-4 py-2 font-medium">
                {col.name}
                {col.type && (
                  <span className="ml-1 text-gray-400 font-normal lowercase">{col.type}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-t border-gray-100 hover:bg-gray-50">
              {row.map((v, ci) => (
                <td key={ci} className="px-4 py-2 font-mono text-xs text-gray-600">
                  {v === null || v === undefined ? 'NULL' : String(v)}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-4 text-center text-gray-400 text-xs">
                Empty result
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
