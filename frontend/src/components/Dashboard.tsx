import { useAuthStore } from "../store/authStore";
import { FileList } from "./FileList";
import { FileUploadModal } from "./FileUploadModal";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { useState } from "react";
import { Plus, User } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Switch } from "@/components/ui/switch";
import { authService } from "../services/authService";
import { UserManagement } from "./UserManagement";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";

export const Dashboard = () => {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleMFAToggle = async () => {
    try {
      const response = await authService.toggleMFA();
      setMfaEnabled(response.mfa_enabled);
    } catch (error) {
      console.error("Failed to toggle MFA:", error);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await authService.deleteAccount();
      logout();
    } catch (error) {
      console.error("Failed to delete account:", error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
        <Card className="shadow-sm">
          <div className="flex justify-between items-center h-16 px-4">
            <h1 className="text-xl font-semibold">SecureShare</h1>
            <div className="flex items-center space-x-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="flex items-center space-x-2"
                  >
                    <User className="h-4 w-4" />
                    <span>{user?.username}</span>
                    <Badge variant="outline" className="ml-2 capitalize">
                      {user?.role}
                    </Badge>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="p-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">
                        Two-Factor Auth
                      </label>
                      <Switch
                        checked={mfaEnabled}
                        onCheckedChange={handleMFAToggle}
                      />
                    </div>
                  </div>
                  <DropdownMenuItem
                    onClick={() => setShowDeleteConfirm(true)}
                    className="text-red-600"
                  >
                    Delete Account
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={logout}>Logout</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </Card>
      </div>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Files</h2>
            {user?.role !== 'guest' && (
              <Button onClick={() => setIsUploadModalOpen(true)}>
                <Plus className="mr-2 h-4 w-4" /> Upload File
              </Button>
            )}
          </div>
          <FileList />
          {user?.role !== 'guest' && (
            <FileUploadModal
              isOpen={isUploadModalOpen}
              onClose={() => setIsUploadModalOpen(false)}
            />
          )}
          {user?.role === "admin" && (
            <div className="mt-8">
              <UserManagement />
            </div>
          )}
        </div>
      </main>
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your
              account and all associated data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAccount}
              className="bg-red-600"
            >
              Delete Account
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
