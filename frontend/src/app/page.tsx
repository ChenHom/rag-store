import Link from "next/link";

export default function HomePage() {
  return (
    <div className="container mx-auto text-center mt-20">
      <h1 className="text-4xl font-bold mb-4">Welcome to RAG Store</h1>
      <p className="text-lg text-gray-600 mb-8">
        Your personal assistant to chat with your documents.
      </p>
      <div className="space-x-4">
        <Link href="/chat" className="btn btn-primary">
          Start Chatting
        </Link>
        <Link href="/upload" className="btn btn-secondary">
          Upload a Document
        </Link>
      </div>
    </div>
  );
}

