/**
 * Task 1 placeholder shell.
 *
 * Intentionally unstyled: the UI rules for this repo are plain tables/lists,
 * no styling polish. Task 59 replaces this with the Intake <-> CaseView router.
 */
export default function App() {
  return (
    <main>
      <h1>GHOST THREAD</h1>
      <p>Agentic OSINT gap-detection system. Scaffold only — no agent logic yet.</p>
      <ul>
        <li>
          API health: <code>/api/health</code> (proxied to the FastAPI service)
        </li>
        <li>Intake and case views arrive in Task 59.</li>
      </ul>
    </main>
  );
}
