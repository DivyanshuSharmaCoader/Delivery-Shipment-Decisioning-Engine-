import { Api } from "./client";

const api = new Api({
  baseURL: "https://fastship-backend-1-0-px6z.onrender.com",
  securityWorker: (token) => {
    if (token) {
      return {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      };
    }
    return {};
  },
});

export default api;