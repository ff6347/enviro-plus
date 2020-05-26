import { nexusPrismaPlugin } from "nexus-prisma";
import { intArg, makeSchema, objectType, stringArg } from "@nexus/schema";

const Collector = objectType({
  name: "Collector",
  definition(t) {
    t.model.id();
    // t.model.createdAt()
    t.model.description();
    t.model.name();
    t.model.records({ type: "Record" });
  },
});

const Record = objectType({
  name: "Record",
  definition(t) {
    t.model.id();
    // t.model.recordedAt();
    t.model.pressure();
    t.model.temperature();
    t.model.humidity();
    t.model.light();
    t.model.nh3();
    t.model.oxidising();
    t.model.reducing();
    t.model.pm1();
    t.model.pm10();
    t.model.pm2_5();
    t.model.noise();
    t.model.collector();
    t.model.collectorId();
  },
});

const Query = objectType({
  name: "Query",
  definition(t) {
    t.crud.collector();
    t.crud.record();
    t.list.field("records", {
      type: "Record",
      resolve: (_, _args, ctx) => {
        return ctx.prisma.record.findMany();
      },
    });
    t.list.field("collectors", {
      type: "Collector",
      resolve: (_, _args, ctx) => {
        return ctx.prisma.collector.findMany();
      },
    });
    t.field("info", {
      type: "String",
      resolve() {
        return "info";
      },
    });
    // t.string("info", () => "info");
  },
});

const Mutation = objectType({
  name: "Mutation",
  definition(t) {
    t.crud.createOneCollector({ alias: "insertCollector" });
    t.crud.createOneRecord({ alias: "insertRecord" });
  },
});

export const schema = makeSchema({
  types: [Collector, Record, Query, Mutation],
  plugins: [nexusPrismaPlugin()],
  outputs: {
    schema: __dirname + "/../../schema.graphql",
    typegen: __dirname + "/generated/nexus.ts",
  },
  typegenAutoConfig: {
    contextType: "Context.Context",
    sources: [
      {
        source: "@prisma/client",
        alias: "prisma",
      },
      {
        source: require.resolve("./context"),
        alias: "Context",
      },
    ],
  },
});
