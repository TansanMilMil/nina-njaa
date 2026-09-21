import { Fragment } from 'react'

const URL_PATTERN = /(https?:\/\/[^\s]+)/g

export default function LinkifiedText({ text }: { text: string }) {
  const parts = text.split(URL_PATTERN)

  return (
    <>
      {parts.map((part, i) =>
        i % 2 === 1 ? (
          <a
            key={i}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline break-all"
          >
            {part}
          </a>
        ) : (
          <Fragment key={i}>{part}</Fragment>
        )
      )}
    </>
  )
}
