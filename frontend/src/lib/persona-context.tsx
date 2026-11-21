"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, errorMessage, type PersonaSummary } from "./api";

const STORAGE_KEY = "wingmate.persona";
export const DEFAULT_PERSONA = "rachel";

type Ctx = {
  personaId: string;
  setPersonaId: (id: string) => void;
  personas: PersonaSummary[];
  personasError: string | null;
};

const PersonaContext = createContext<Ctx | null>(null);

export function PersonaProvider({ children }: { children: React.ReactNode }) {
  const [personaId, setId] = useState(DEFAULT_PERSONA);
  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [personasError, setPersonasError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) setId(saved);
    } catch {
      // storage unavailable
    }
    api
      .personas()
      .then((list) => {
        setPersonas(list);
        setPersonasError(null);
      })
      .catch((e) => setPersonasError(errorMessage(e)));
  }, []);

  const setPersonaId = useCallback((id: string) => {
    setId(id);
    try {
      window.localStorage.setItem(STORAGE_KEY, id);
    } catch {
      // storage unavailable
    }
  }, []);

  return (
    <PersonaContext.Provider value={{ personaId, setPersonaId, personas, personasError }}>
      {children}
    </PersonaContext.Provider>
  );
}

export function usePersona(): Ctx {
  const ctx = useContext(PersonaContext);
  if (!ctx) throw new Error("usePersona must be used inside PersonaProvider");
  return ctx;
}
