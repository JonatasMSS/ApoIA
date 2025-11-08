export default async function (app: any) {
  app.get("/", async () => {
    return { Ok: true, message: "WhatsBot API está funcionando!" };
  });
}
