import { useState } from "react";
import { useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "../components/ui/card";
import { fileService } from "../services/fileService";

export const SharedFilePage = () => {
  const { token } = useParams();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleDownload = async () => {
    if (!password) {
      setError("Please enter the file password");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const blob = await fileService.accessSharedFile(token!, password);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "shared-file"; // The actual filename will be set by the server
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      setError(error.response?.data?.detail || "Failed to access file");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container max-w-md mt-10">
      <Card>
        <CardHeader>
          <h1 className="text-2xl font-bold">Access Shared File</h1>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter file password"
            />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </CardContent>
        <CardFooter>
          <Button
            onClick={handleDownload}
            disabled={isLoading}
            className="w-full"
          >
            {isLoading ? "Accessing..." : "Access File"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
