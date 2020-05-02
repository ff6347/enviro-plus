import { GraphQLServer } from "graphql-yoga";
import { schema } from "./lib/schema";
import cors from "cors";

import { createContext } from "./lib/context";
// const prisma = new PrismaClient();

// import * as Query from "./lib/resolvers/queries";
// const resolvers = {
//   Query,
// };
const server = new GraphQLServer({
  schema,
  context: createContext,
});

server.use(cors());

server.start(() => {
  console.log("running on http://localhost:4000");
});
// async function main() {
//   const collectors = await prisma.collector.findMany();
//   console.log(collectors);
// }
// main()
//   .catch((e) => {
//     throw e;
//   })
//   .finally(async () => {
//     await prisma.disconnect();
//   });
