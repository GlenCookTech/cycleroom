import Link from "next/link";
import "../styles/globals.css";

export default function MyApp({ Component, pageProps }) {
  return (
    <div>
      <nav>
        <Link href="/">Dashboard</Link> | 
        <Link href="/sessions"> Sessions</Link> | 
        <Link href="/leaderboard"> Leaderboard</Link>
      </nav>
      <Component {...pageProps} />
    </div>
  );
}
