from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "Users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "Conversations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "window_size" INT NOT NULL DEFAULT 0,
    "title" TEXT NOT NULL,
    "is_bookmarked" BOOL NOT NULL DEFAULT False,
    "user_id" UUID NOT NULL REFERENCES "Users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "Messages" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "role" VARCHAR(6) NOT NULL,
    "conversation_id" UUID NOT NULL REFERENCES "Conversations" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "Messages"."role" IS 'USER: user\nSYSTEM: system\nAI: ai';
CREATE TABLE IF NOT EXISTS "ConversationsSummary" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "summary" TEXT NOT NULL,
    "summary_level" SMALLINT NOT NULL DEFAULT 0,
    "conversation_id" UUID NOT NULL REFERENCES "Conversations" ("id") ON DELETE CASCADE,
    "last_message_id" INT NOT NULL REFERENCES "Messages" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmmtv4jgUhv9KlE8dqVu1tNOOqtVKgdIddrisuOzcFZnEgEXiMLEzlK3639c2ucehoc"
    "AA23xpm2OfJH7OsfMeu4+q7ZjQImc1B/+ELgEUOVi9VR5VDGzI/pC2nyoqmM2iVm6gYGgJ"
    "h3hP0QKGhLrAoKxxBCwCmcmExHDRzH8Y9iyLGx2DdUR4HJk8jH54UKfOGNIJdFnD1+/MjL"
    "AJHyAJLmdTfYSgZSbeG5n82cKu08VM2AaDxt296MkfN9QNx/JsHPWeLejEwWF3z0PmGffh"
    "bWOIoQsoNGPD4G/pDzswLd+YGajrwfBVzchgwhHwLA5D/X3kYYMzUMST+I+rP9Q18BiMME"
    "OLMOUsHp+Wo4rGLKyqCMp7rXtyef1GjNIhdOyKRkFEfRKOgIKlq+AagTRcyIetA5oFesda"
    "KLKhHGrSMwXX9F3Pgj9eAjkwRJSjDAswB/hexlRlYzA72Fr4EVzBuN9o1Xt9rfU3H4lNyA"
    "9LINL6dd5SEdZFynqyDInD5sdy9oQ3UT42+u8Vfql86bTr6cCF/fpfVP5OwKOOjp25DsxY"
    "sgXWAAzrGQXWm5kvDGzSswzsXgPrv3wU1zmDxvoT9C/MBraBqTymKa9UUBm1XYXxfIMYjv"
    "lDfqtcXN1cvbu8vnrHuogXCS03K8LaaPfF0heRo4haEmZ9+JADLXRI4WIveZhZvyrL65/6"
    "iQRv/6N1xXejpX16k0jyZqf9Z9A9yvB2rdmppogiog8dZ2oDdwolH+Sq41gQ4Jxvcto3BZ"
    "k1WruivK5QKY652uk0E5irjTTHQata755cCOasE6JQnq4ega6+ns6JuWxT7Ow1cZ/RNlwh"
    "jqZSacNpZOndOy5EY/wBLgTDBnsPgA3ZNPe18cC/zcFSi6zRF8QF81A1x9OCDY8NCi5zrq"
    "b1atpdXRUQh8CYzoFr6jk0iWezuYogkcxz3/X+QxdaYQ0hpxmvH3rilovjgpuYozYkBIw3"
    "ZdJa3uXIOPCkcSpOLFkSaZRtsit22gIwG7fpP5s/aUWWPFO2xpKpYPUa9yiL2LKILWudso"
    "gtA/tLilgSLb1Fi7GYS1mOycsxH5FuwZ/QyrLt2cCycncIMs7HtEdwWbm5DrcH+MWqnYFe"
    "S2s2s/WWEdMGa9ZdEtfXUn/FCVqAUN2XxFKCuckn8fx16bfhIr2FXaoVRayROpnZsJhNH/"
    "QcHs+iRa1kzsmL27wM3QLNoyzc0iAlc2/dXYJdloIBY0n5F8OfX/K1YiX64ZR5uSth0cXP"
    "j+Rm5d3+V77Tsqr7v4v/bFVHmchf6xzG71/qfrnudx3ZuVZtAtw69uzMtyzBNvDdM1t10K"
    "t3bxW+U/0N9z73+vXWrUIWhEL7G9YatwpAarFpY4MHVsPgMZ2wy+sVoQjApydCEJEKbylL"
    "hJ0e0ZTqNkeUFVa35dFNccg7PbIQx4QSkRocH+YrVN7jwORpeQpRnkKUejUIrPgt1VfycA"
    "b9j0WvJjVT5e3bAqqJ9crVTaItqZygDZBkSzqfYeiwHYg7r4V3j3AGCJk7rmS1zqcY93nl"
    "2ZhRoUWUk5H+b/ftqKfDBL8X2aRBFxkTmXDyW1ZKJxD1ORjtVG7tPb+1x2eCtOTLX8piLq"
    "98JYt/FPjUWAOi3/04AV6cnxcAyHrlAhRtmS0dCrFEsf/V67Rzt3IClxTIAWYD/Goig54q"
    "FiL0+2FiXUGRj3r1/mR6KzIlt/kNqut9brf/eXn6D1m7ypw="
)
