import React, { useState } from 'react';
import { useFileStore } from '../../store/fileStore';

export const FileUpload = () => {
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState('');
  const { uploadFile, isLoading, error } = useFileStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (file && password) {
      await uploadFile(file, password);
      setFile(null);
      setPassword('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Select File
        </label>
        <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mt-1 block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-indigo-50 file:text-indigo-700
            hover:file:bg-indigo-100"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Encryption Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button
        type="submit"
        disabled={!file || !password || isLoading}
        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
      >
        {isLoading ? 'Uploading...' : 'Upload File'}
      </button>
    </form>
  );
};
