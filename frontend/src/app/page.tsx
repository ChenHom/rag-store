import Link from "next/link";

export default function HomePage() {
  return (
    <div className="container mx-auto text-center mt-20">
      <h1 className="text-4xl font-bold mb-4">Welcome to RAG Store</h1>
      <p className="text-lg text-gray-600 mb-8">
        Your personal assistant to chat with your documents.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <Link href="/chat" className="btn btn-primary">
          基礎問答
        </Link>
        <Link href="/upload" className="btn btn-secondary">
          上傳文件
        </Link>
        <Link href="/search" className="btn btn-info">
          進階搜尋
        </Link>
        <Link href="/classification" className="btn btn-success">
          分類管理
        </Link>
      </div>
    </div>
  );
}

