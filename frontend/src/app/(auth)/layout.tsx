"""
Auth layout with side-by-side design.
"""

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      <div className="flex-1 bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-8">
        <div className="text-white max-w-md">
          <h1 className="text-4xl font-bold mb-4">MemoryOS</h1>
          <p className="text-lg opacity-90">
            Your AI-powered personal knowledge operating system
          </p>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        {children}
      </div>
    </div>
  );
}
