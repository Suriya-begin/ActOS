import { create } from "zustand"

interface Command {
  id: string; text: string; intent: string; status: string; timestamp: Date
}

interface ActOSStore {
  commands:     Command[]
  agentStatus:  Record<string, string>
  isListening:  boolean
  addCommand:   (cmd: Command) => void
  setListening: (v: boolean) => void
  setAgentStatus: (agent: string, status: string) => void
}

export const useActOSStore = create<ActOSStore>((set) => ({
  commands:    [],
  agentStatus: { messaging: "online", browser: "busy", calendar: "online", research: "offline", email: "online" },
  isListening: false,
  addCommand:  (cmd) => set((s) => ({ commands: [cmd, ...s.commands].slice(0, 50) })),
  setListening: (v) => set({ isListening: v }),
  setAgentStatus: (agent, status) => set((s) => ({ agentStatus: { ...s.agentStatus, [agent]: status } })),
}))
