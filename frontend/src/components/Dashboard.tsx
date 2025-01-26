import { useAuthStore } from "../store/authStore";
import { FileList } from "./FileList";
import { FileUploadModal } from "./FileUploadModal";
import { Button } from "./ui/button";
import { useState } from "react";
import { Plus } from "lucide-react";

export const Dashboard = () => {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold">SecureShare</h1>
            <div className="flex items-center space-x-4">
              <span className="text-muted-foreground">
                Welcome, {user?.username}
              </span>
              <Button variant="outline" onClick={logout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-3xl font-bold">Files</h2>
            <Button onClick={() => setIsUploadModalOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> Upload File
            </Button>
          </div>
          <FileList />
          <FileUploadModal
            isOpen={isUploadModalOpen}
            onClose={() => setIsUploadModalOpen(false)}
          />
        </div>
      </main>
    </div>
  );
};
