import { MessageSquare, FileText, User, Activity, BookOpen } from "lucide-react"

interface EmptyConversationProps {
  onSelect: (text: string) => void
}

export function EmptyConversation({ onSelect }: EmptyConversationProps) {
  const cards = [
    {
      title: "Summarize my documents",
      icon: FileText,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      title: "What do you know about me?",
      icon: User,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      title: "Analyze my knowledge gaps",
      icon: Activity,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
    },
    {
      title: "Help me learn about a topic",
      icon: BookOpen,
      color: "text-cyan-500",
      bg: "bg-cyan-500/10",
    },
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full w-full max-w-2xl mx-auto px-4 py-12 md:py-24 text-center animate-in fade-in zoom-in-95 duration-500">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-zinc-800/50 border border-zinc-800">
        <MessageSquare className="h-8 w-8 text-zinc-400" />
      </div>
      
      <h1 className="mb-3 text-3xl font-semibold tracking-tight text-zinc-100">
        Start a conversation
      </h1>
      
      <p className="mb-12 text-zinc-400 max-w-md">
        Ask anything about your documents, knowledge, or memories. 
        I'll search, analyze, and answer with sources.
      </p>

      <div className="grid w-full grid-cols-1 sm:grid-cols-2 gap-4">
        {cards.map((card, i) => (
          <button
            key={i}
            onClick={() => onSelect(card.title)}
            className="group flex flex-col items-start gap-4 rounded-xl border border-zinc-800 bg-transparent p-5 text-left transition-all hover:bg-zinc-900"
          >
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${card.bg}`}>
              <card.icon className={`h-5 w-5 ${card.color}`} />
            </div>
            <span className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100">
              {card.title}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
